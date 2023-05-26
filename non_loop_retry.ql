/**
 * @kind problem
 * @id WHEN-too-soon 
 * @problem.severity warning
 */

import java
import semmle.code.java.ControlFlowGraph

class GithubLocation extends Location {
  string getGithubURL() {
  	result = "https://github.com/%%GITHUB_NAMESPACE%%/tree/" + "/" + 
				"%%COMMIT_SHA%%" + "/" + 
				this.toString().replaceAll("file:///opt/src", "").regexpReplaceAll(":(\\d+):\\d+:\\d+:\\d+$", "#L$1")
  }
}

predicate isRetryLoop(LoopStmt l) {

  (not l instanceof EnhancedForStmt)
		and
  (exists(Expr e | e.getAnEnclosingStmt() = l and (e instanceof VarAccess or e instanceof MethodAccess) and
                        (e.toString().toLowerCase().matches("%retry%") or e.toString().toLowerCase().matches("%retries%")))

        or
    exists (StringLiteral s | s.getAnEnclosingStmt() = l and (s.getValue().matches("%retry%") or s.getValue().matches("%retries%"))))
	and
  (hasExceptionHandling(l) or exists(Exception e | e.getName() != "InterruptedException" and e = l.getEnclosingCallable().getAnException()))
  
}

predicate hasExceptionHandling(Stmt s) {
	exists(CatchClause cc | not cc.getACaughtType().toString().matches("%InterruptedException%") and cc.getEnclosingStmt*() = s)
}

predicate isSource(Element e) {
 not e.getCompilationUnit().getFile().getRelativePath().toLowerCase().matches("%test%") 
}


from Expr e 
where isSource(e) and
	e.toString().toLowerCase().matches("%retry%") or e.toString().toLowerCase().matches("%retries%") and
	not exists(LoopStmt loop | isRetryLoop(loop) and (e.getAnEnclosingStmt()=loop or e.getEnclosingCallable() = loop.getEnclosingCallable())) 
select e.getEnclosingCallable().getLocation().(GithubLocation).getGithubURL()
