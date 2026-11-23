package delegated;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.Set;
import org.eventb.core.ast.*;
import org.eventb.core.seqprover.*;
import org.eventb.core.seqprover.eventbExtensions.Tactics;

/** A uniform automatic strategy: no PO-name tests, no Review and no oracle. */
public class AutomaticTactic implements ITactic {
 private void each(IProofTreeNode root,ITactic t,IProofMonitor monitor){
  for(var leaf:root.getOpenDescendants()){
   if(monitor!=null&&monitor.isCanceled())return;
   t.apply(leaf,monitor);
  }
 }
 private void selectAll(IProofTreeNode root,IProofMonitor monitor){
  for(int pass=0;pass<2;pass++){
   for(var leaf:root.getOpenDescendants()){
    var hs=new ArrayList<Predicate>();for(var h:leaf.getSequent().hypIterable())hs.add(h);
    var action=pass==0?ProverFactory.makeShowHypAction(hs):ProverFactory.makeSelectHypAction(hs);
    Tactics.mngHyp(action).apply(leaf,monitor);
   }
  }
 }
 private void selectRelevant(IProofTreeNode root,IProofMonitor monitor){
  // Hypothesis-management tactics create child nodes; refresh leaves between passes.
  for(int pass=0;pass<2;pass++){
   for(var leaf:root.getOpenDescendants()){
    var hs=new ArrayList<Predicate>();for(var h:leaf.getSequent().hypIterable())hs.add(h);
    if(pass==0){Tactics.mngHyp(ProverFactory.makeDeselectHypAction(hs)).apply(leaf,monitor);continue;}
    var allowed=new HashSet<String>(Set.of("NODE","CAP","JOB","root","rootScope","parent","rank","path","owner","need","budget","issued","pending","committed","submitted","j","a","R","T"));
    for(var id:leaf.getSequent().goal().getFreeIdentifiers())allowed.add(id.getName());
    var relevant=new ArrayList<Predicate>();
    for(var h:hs){boolean accept=true;for(var id:h.getFreeIdentifiers())if(!allowed.contains(id.getName()))accept=false;if(accept)relevant.add(h);}
    Tactics.mngHyp(ProverFactory.makeSelectHypAction(relevant)).apply(leaf,monitor);
   }
  }
 }
 private IPosition locate(Formula<?> f,Expression target,IPosition pos){
  if(f.equals(target))return pos;
  for(int i=0;i<f.getChildCount();i++){var found=locate(f.getChild(i),target,pos.getChildAtIndex(i));if(found!=null)return found;}
  return null;
 }
 private Object contextualRewrite(IProofTreeNode node,IProofMonitor monitor){
  for(var h:node.getSequent().hypIterable()){
   if(!(h instanceof RelationalPredicate)||h.getTag()!=Formula.EQUAL)continue;
   var eq=(RelationalPredicate)h;
   if(eq.getLeft() instanceof FreeIdentifier)continue;
   var pos=locate(node.getSequent().goal(),eq.getLeft(),FormulaFactory.makePosition(""));
   if(pos!=null){
    Object result=Tactics.localEqRewrite(null,pos,h).apply(node,monitor);
    if(result==null)return null;
    result=Tactics.eqE(h).apply(node,monitor);
    if(result==null)return null;
   }
  }
  return "no contextual equality rewrite";
 }
 public Object apply(IProofTreeNode root,IProofMonitor monitor){
  var reg=SequentProver.getAutoTacticRegistry();
  ITactic strongML=null;
  if(reg.isRegisteredParameterizer("com.clearsy.atelierb.provers.core.mlParam")){
   var pd=reg.getParameterizerDescriptor("com.clearsy.atelierb.provers.core.mlParam");
   var values=pd.makeParameterSetting();values.setInt("forces",3);values.setLong("timeout",2000L);values.setBoolean("restricted",false);
   strongML=pd.instantiate(values,"DelegatedML2000").getTacticInstance();
  }
  var pp=reg.getTacticDescriptor("org.eventb.pp.ppUnrestricted").getTacticInstance();
  String[] ids={"clarifyGoalTac","forallGoalTac","impGoalTac","conjGoalTac","funOvrGoalTac","funGoalTac","mbGoalTac","finiteInclusionTac","funAppInDomGoalTac","genMPTac"};
  for(int round=0;round<3&&root.getOpenDescendants().length>0;round++){
   selectAll(root,monitor);
   each(root,Tactics.hyp(),monitor);
   each(root,(node,m)->contextualRewrite(node,m),monitor);
   each(root,Tactics.autoRewrite(),monitor);
   each(root,(node,m)->{
    var positions=Tactics.setEqlGetPositions(node.getSequent().goal());
    if(positions.isEmpty())return "not a set equality";
    return Tactics.setEqlRewrites(null,positions.get(0)).apply(node,m);
   },monitor);
   for(String id:ids){
    String full="org.eventb.core.seqprover."+id;
    if(reg.isRegistered(full))each(root,reg.getTacticDescriptor(full).getTacticInstance(),monitor);
   }
   each(root,(node,m)->{
    String goal=node.getSequent().goal().toString();
    if(!goal.startsWith("finite(")||goal.equals("finite(JOB)"))return "not a finite job subset";
    return Tactics.finiteSet(node.getSequent(),"JOB").apply(node,m);
   },monitor);
   each(root,Tactics.hyp(),monitor);
   each(root,(node,m)->{
    var positions=Tactics.cardComparisonGetPositions(node.getSequent().goal());
    if(positions.isEmpty())return "not a cardinality comparison";
    return Tactics.cardComparison(null,positions.get(0)).apply(node,m);
   },monitor);
   selectRelevant(root,monitor);
   for(String external:new String[]{"ml","p1","pp"}){
    String id="com.clearsy.atelierb.provers.core."+external;
    if(reg.isRegistered(id))each(root,reg.getTacticDescriptor(id).getTacticInstance(),monitor);
   }
   if(strongML!=null)each(root,strongML,monitor);
   for(var leaf:root.getOpenDescendants()){
    pp.apply(leaf,monitor);
   }
  }
  return root.getOpenDescendants().length==0?null:"automatic strategy left subgoals";
 }
}
