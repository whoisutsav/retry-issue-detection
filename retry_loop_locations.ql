/**
 * @kind problem
 * @id WHEN-too-soon 
 * @problem.severity warning
 */

import java
import semmle.code.java.ControlFlowGraph

string appName() {
	result="%%GITHUB_NAMESPACE%%_%%COMMIT_SHA%%"
}

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

// Returns line numbers that are inside a catch block
string linesInsideCatch(LoopStmt loop) {
	result=concat(int i | 
			i in [loop.getLocation().getStartLine() .. loop.getBody().getLocation().getEndLine()] and
			exists(Stmt s, CatchClause cc | 
					s.getEnclosingStmt*()=loop and 
					cc.getEnclosingStmt*() = loop and s.getEnclosingStmt*() = cc and 
					s.getLocation().getStartLine()<=i and
					s.getLocation().getEndLine()>=i)
			| i.toString(), ";")
}

from LoopStmt loop
where isRetryLoop(loop) and isSource(loop)
select appName(), 
		loop.getLocation().(GithubLocation).getGithubURL(),
        loop.getLocation().getFile().getRelativePath(),
		loop.getCompilationUnit().getPackage().getName(),
        loop.getLocation().getStartLine(),
        loop.getBody().getLocation().getEndLine(),
		linesInsideCatch(loop)
