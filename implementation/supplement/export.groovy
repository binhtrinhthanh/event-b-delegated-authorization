import com.google.inject.Guice
import de.prob.MainModule
import de.prob.scripting.Api
def api = Guice.createInjector(new MainModule()).getInstance(Api)
def space = api.eventb_load(args[0], ['MAX_OPERATIONS':'1000'])
api.eventb_save(space, args[1])
System.exit(0)
