/**
 * @kind problem
 * @id WHEN-too-soon 
 * @problem.severity warning
 */

import java

class GithubLocation extends Location {
  string getGithubURL() {
  	result = "https://github.com/%%GITHUB_NAMESPACE%%/tree/" + "/" + 
				"%%COMMIT_SHA%%" + "/" + 
				this.toString().replaceAll("file:///opt/src", "").regexpReplaceAll(":(\\d+):\\d+:\\d+:\\d+$", "#L$1")
  }
}

predicate isRetryLoop(LoopStmt l) {

  /*
    exists (Expr e | e.getAnEnclosingStmt() = l and
                        (e instanceof VarAccess or e instanceof MethodAccess) and
                        e.toString().toLowerCase().matches("%retry%") or e.toSstring().toLowerCase().matches("%retries%"))

        or
    exists (StringLiteral s | s.getAnEnclosingStmt() = l and s.getValue().matches("%retry%") or s.getValue().matches("%retries%"))
  */

  (not l instanceof EnhancedForStmt)
    and
  exists(Expr e | e.getAnEnclosingStmt() = l and (e.toString().toLowerCase().matches("%retry%") or e.toString().toLowerCase().matches("%retries%")))
	and
  (hasExceptionHandling(l) or exists(Exception e | e.getName() != "InterruptedException" and e = l.getEnclosingCallable().getAnException()))
}

predicate hasExceptionHandling(Stmt s) {
	exists(CatchClause cc | not cc.getACaughtType().toString().matches("%InterruptedException%") and cc.getEnclosingStmt*() = s)
}

predicate isSleepMethod(MethodAccess m) {
	m.getMethod().hasQualifiedName("java.lang", "Thread", "sleep") or
	m.getMethod().hasQualifiedName("java.util.concurrent", "TimeUnit", "sleep") 
}

predicate hasSleep(Stmt s) {
  exists(MethodAccess m | isSleepMethod(m) and m.getAnEnclosingStmt() = s) 
}

predicate isSource(Element e) {
 not e.getCompilationUnit().getFile().getRelativePath().toLowerCase().matches("%test%") 
}

predicate isJavaMethod(Method m) {
  m.getQualifiedName().matches("java%") or m.getQualifiedName().matches("%slf4j%")
}


from LoopStmt l 
where isRetryLoop(l) and
not hasSleep(l) and 
not exists(MethodAccess ma | ma.getAnEnclosingStmt() = l and hasSleep(ma.getMethod().getAPossibleImplementation().getBody())) and 
isSource(l)
select l.getLocation().(GithubLocation).getGithubURL()
