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
  

  /*
  (not l instanceof EnhancedForStmt)
    and
  exists(Expr e | e.getAnEnclosingStmt() = l and (e.toString().toLowerCase().matches("%retry%") or e.toString().toLowerCase().matches("%retries%")))
	and
  (hasExceptionHandling(l) or exists(Exception e | e.getName() != "InterruptedException" and e = l.getEnclosingCallable().getAnException()))*/
}

predicate hasExceptionHandling(Stmt s) {
	exists(CatchClause cc | not cc.getACaughtType().toString().matches("%InterruptedException%") and cc.getEnclosingStmt*() = s)
}

predicate isSource(Element e) {
 not e.getCompilationUnit().getFile().getRelativePath().toLowerCase().matches("%test%") 
}

predicate isJavaMethod(Method m) {
  m.getQualifiedName().matches("java%") or m.getQualifiedName().matches("%slf4j%")
}

predicate isCaughtTopLevel(LoopStmt loop, CatchClause cc) {
	cc.getEnclosingStmt*() = loop
			and
	not exists(CatchClause cc2 | cc != cc2 and cc2.getEnclosingStmt*() = loop and cc.getEnclosingStmt*() = cc2.getBlock())

}

predicate exprSucceedsNode(ControlFlowNode node, Expr expr) {
	node.getASuccessor().(Expr).getParent*() = expr
		or
	exprSucceedsNode(node.getANormalSuccessor(), expr)
}

predicate isRetried(LoopStmt loop, RefType ex) {
	exists(CatchClause cc | isCaughtTopLevel(loop,cc) 
			and
			cc.getACaughtType() = ex 
			and
			exists(Expr loopReentry, ControlFlowNode last | 
				if exists(loop.(ForStmt).getAnUpdate())
				then loopReentry = loop.(ForStmt).getUpdate(0)
				else loopReentry = loop.getCondition() 
			|
				last.getEnclosingStmt().getEnclosingStmt*() = cc.getBlock() and
				exprSucceedsNode(last, loopReentry)
				//last.getASuccessor().(Expr).getParent*() = loopReentry
			))
			
}

predicate isNotRetried(LoopStmt loop, RefType ex) {
	exists(CatchClause cc | isCaughtTopLevel(loop,cc) 
			and
			cc.getACaughtType() = ex 
			and
			not exists(Expr loopReentry, ControlFlowNode last | 
				if exists(loop.(ForStmt).getAnUpdate())
				then loopReentry = loop.(ForStmt).getUpdate(0)
				else loopReentry = loop.getCondition() 
			|
				last.getEnclosingStmt().getEnclosingStmt*() = cc.getBlock() and
				exprSucceedsNode(last, loopReentry)
				//last.getASuccessor().(Expr).getParent*() = loopReentry
			))
}

predicate isNotRetriedImplicit(LoopStmt loop, RefType ex) {
	exists(MethodAccess ma | ma.getAnEnclosingStmt() = loop and ma.getMethod().getAThrownExceptionType() = ex and
			not exists(CatchClause cc | cc.getEnclosingStmt*() = loop and cc.getACaughtType().getADescendant() = ex))
			
}


string allRetriedExceptions(LoopStmt l) {
	result = concat(RefType t | isRetried(l,t) | t.toString(), " | ")
}

string allNotRetriedExceptions(LoopStmt l) {
	result = concat(RefType t | isNotRetried(l,t) | t.toString(), " | ")
}

string allNotRetriedImplicitExceptions(LoopStmt l) {
	result = concat(RefType t | isNotRetriedImplicit(l,t) | t.toString(), " | ")
}


from LoopStmt l 
where 
	isSource(l)
		and
	isRetryLoop(l)
select l.getLocation().(GithubLocation).getGithubURL(), allRetriedExceptions(l), allNotRetriedExceptions(l), allNotRetriedImplicitExceptions(l)
