#!/usr/bin/env python3
"""Compile the included batch application against an existing Rodin install.
Uses an isolated OSGi configuration, workspace and plugin directory.
Requires JDK17+, Rodin3.8+, and the installation's native libraries.
"""
import argparse,subprocess,shutil,os,zipfile
from pathlib import Path
BASE=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('--rodin',required=True,type=Path);p.add_argument('--work',required=True,type=Path);p.add_argument('--log',type=Path);p.add_argument('--source',type=Path);p.add_argument('--ecj',type=Path,help='optional Eclipse compiler JAR when javac is unavailable');args=p.parse_args()
rodin=args.rodin.resolve();work=args.work.resolve();work.mkdir(parents=True,exist_ok=True)
plugins=rodin/'plugins';jars=sorted(plugins.glob('*.jar'))
assert jars,'No plugins/*.jar in given Rodin installation'
classes=work/'classes';classes.mkdir(exist_ok=True)
cp=os.pathsep.join(map(str,jars))
source=BASE/'tools/headless/src/delegated/BuildDelegation.java'
compiler=['java','-jar',str(args.ecj),'-17'] if args.ecj else ['javac']
subprocess.run(compiler+['-cp',cp,'-d',str(classes),*[str(x) for x in source.parent.glob('*.java')]],check=True)
plugin=work/'delegated.batch_1.0.0.jar'
with zipfile.ZipFile(plugin,'w') as jar:
    jar.write(BASE/'tools/headless/META-INF/MANIFEST.MF','META-INF/MANIFEST.MF')
    jar.write(BASE/'tools/headless/plugin.xml','plugin.xml')
    for f in classes.rglob('*.class'):jar.write(f,str(f.relative_to(classes)))
config=work/'configuration';shutil.copytree(rodin/'configuration',config,dirs_exist_ok=True)
# The copied installation configuration resolves relative URLs against the
# original install area supplied below. Add only the task's private bundle.
info=config/'org.eclipse.equinox.simpleconfigurator/bundles.info'
with info.open('a') as f:f.write('\ndelegated.batch,1.0.0,'+plugin.as_uri()+',4,false\n')
launcher=sorted(plugins.glob('org.eclipse.equinox.launcher_*.jar'))[0]
cmd=['java','-Xmx1536m','-Dosgi.requiredJavaVersion=17','-jar',str(launcher),'-install',str(rodin),'-configuration',str(config),'-data',str(work/'workspace'),'-application','delegated.batch.build','-nosplash','-consoleLog',str(args.source.resolve() if args.source else BASE/'DelegatedAuthorization')]
log=args.log.resolve() if args.log else work/'rodin_native.log'
print('Native Rodin output:',log,flush=True)
with log.open('w') as f:
 result=subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT)
print('Rodin process exit:',result.returncode,flush=True)
print(log.read_text()[-7000:])
raise SystemExit(result.returncode)
