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

predicate hasExceptionHandling(Stmt s) {
	exists(CatchClause cc | not cc.getACaughtType().toString().matches("%InterruptedException%") and cc.getEnclosingStmt*() = s)
}

predicate isSource(Element e) {
 not e.getCompilationUnit().getFile().getRelativePath().toLowerCase().matches("%test%") 
}

predicate isErrorHandlingBlock(BlockStmt s) {
	exists(CatchClause cc | cc.getBlock() = s)
		or
	exists(Callable c | s.getEnclosingCallable() = c and s = c.getBody() and c.getAParamType().getName() = "Throwable")
}

predicate submitsToQueue(BlockStmt s) {
	exists(MethodAccess ma | 
			ma.getReceiverType().getAnAncestor().hasQualifiedName("java.util.concurrent", "Executor") and
			ma.getAnEnclosingStmt() = s and
			(not ma.getMethod().hasName("shutdown") and not ma.getMethod().hasName("shutdownNow") and not ma.getMethod().hasName("isShutdown")))
}


/*from Callable c
where exists(StringLiteral s | s.getEnclosingCallable() = c and (s.getValue().matches("%retry%") or s.getValue().matches("%retries%"))) and
not exists(LoopStmt s | s.getEnclosingCallable() = c) and
isSource(c)
select c.getLocation().(GithubLocation).getGithubURL()*/

from BlockStmt bs
where isErrorHandlingBlock(bs) and
submitsToQueue(bs) and
isSource(bs)
select bs.getLocation().(GithubLocation).getGithubURL()

