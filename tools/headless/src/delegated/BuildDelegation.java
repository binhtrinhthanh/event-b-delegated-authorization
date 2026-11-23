package delegated;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import org.eclipse.equinox.app.*;
import org.eclipse.core.resources.*;
import org.eclipse.core.runtime.*;
import org.eventb.core.*;
import org.rodinp.core.*;

/** Native Rodin static check, POG and core auto-tactic execution. */
public class BuildDelegation implements IApplication {
 public Object start(IApplicationContext context) throws Exception {
  String[] args=(String[])context.getArguments().get(IApplicationContext.APPLICATION_ARGS);
  if(args.length==0)throw new IllegalArgumentException("source project directory required");
  IWorkspace ws=ResourcesPlugin.getWorkspace();
  IProject project=ws.getRoot().getProject("DelegatedAuthorization");
  if(!project.exists()){
   IProjectDescription d=ws.newProjectDescription("DelegatedAuthorization");
   d.setNatureIds(new String[]{"org.rodinp.core.rodinnature"});
   ICommand cmd=d.newCommand();cmd.setBuilderName("org.rodinp.core.rodinbuilder");d.setBuildSpec(new ICommand[]{cmd});
   project.create(d,null);
  }
  project.open(null);
  try(var paths=Files.list(Path.of(args[0]))){
   for(Path p:paths.toList()){
    String name=p.getFileName().toString();
    if(!name.endsWith(".bum")&&!name.endsWith(".buc"))continue;
    IFile f=project.getFile(name);
    try(var stream=Files.newInputStream(p)){
     if(f.exists())f.setContents(stream,true,false,null);else f.create(stream,true,null);
    }
   }
  }
  var auto=EventBPlugin.getAutoPostTacticManager();
  auto.getAutoTacticPreference().setEnabled(false);
  auto.getPostTacticPreference().setEnabled(false);
  ws.build(IncrementalProjectBuilder.FULL_BUILD,new NullProgressMonitor());
  int errors=0;
  for(IMarker m:project.findMarkers(null,true,IResource.DEPTH_INFINITE)){
   int severity=m.getAttribute(IMarker.SEVERITY,0);
   System.out.println("MARKER "+severity+" "+m.getResource().getName()+" "+m.getAttribute(IMarker.MESSAGE,""));
   if(severity==IMarker.SEVERITY_ERROR)errors++;
  }
  if(errors>0){System.out.println("STATIC_ERRORS "+errors);ws.save(true,null);return 2;}
  System.out.println("STATIC_ERRORS 0");
  auto.getAutoTacticPreference().setEnabled(true);
  var strategy=org.eventb.core.seqprover.SequentProver.getAutoTacticRegistry().getTacticDescriptor("delegated.batch.automatic");
  auto.getAutoTacticPreference().setSelectedDescriptor(strategy);
  var profiles=org.eventb.core.preferences.autotactics.TacticPreferenceFactory.makeTacticPreferenceMap();
  profiles.add("DelegatedAuto",strategy);
  var prefs=new org.eclipse.core.resources.ProjectScope(project).getNode(EventBPlugin.PLUGIN_ID);
  prefs.put(org.eventb.core.preferences.autotactics.TacticPreferenceConstants.P_TACTICSPROFILES,profiles.extract());
  prefs.put(org.eventb.core.preferences.autotactics.TacticPreferenceConstants.P_AUTOTACTIC_CHOICE,"DelegatedAuto");
  prefs.flush();
  IRodinProject rp=RodinCore.valueOf(project);
  List<IEventBRoot> roots=new ArrayList<>();
  roots.addAll(Arrays.asList(rp.getRootElementsOfType(IContextRoot.ELEMENT_TYPE)));
  roots.addAll(Arrays.asList(rp.getRootElementsOfType(IMachineRoot.ELEMENT_TYPE)));
  for(IEventBRoot root:roots){
   IPSRoot ps=root.getPSRoot();
   if(!ps.exists()){System.out.println("NO_PO "+root.getComponentName());continue;}
   org.eventb.internal.core.pom.AutoProver.run(ps.getStatuses(),new NullProgressMonitor());
   int discharged=0,total=ps.getStatuses().length;
   for(IPSStatus status:ps.getStatuses()){
    if(status.getConfidence()>=1000){discharged++;System.out.println("CLOSED "+root.getComponentName()+" "+status.getElementName());}
    else System.out.println("UNPROVED "+root.getComponentName()+" "+status.getElementName());
   }
   System.out.println("RESULT "+root.getComponentName()+" "+discharged+"/"+total);
  }
  org.eclipse.core.runtime.jobs.Job.getJobManager().join(ResourcesPlugin.FAMILY_AUTO_BUILD,new NullProgressMonitor());
  ws.save(true,null);System.out.println("NATIVE_BUILD_COMPLETE");return IApplication.EXIT_OK;
 }
 public void stop(){}
}
