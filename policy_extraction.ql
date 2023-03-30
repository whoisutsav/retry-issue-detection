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

predicate hasSuccessor(ControlFlowNode node, Expr expr) {
	node.getASuccessor().(Expr).getParent*() = expr
		or
	hasSuccessor(node.getANormalSuccessor(), expr)
}

predicate isCaughtExactlyAndRetried(LoopStmt loop, RefType ex) {
	exists(CatchClause cc | isCaughtTopLevel(loop,cc) 
			and
			cc.getACaughtType() = ex 
			and
			exists(MethodAccess ma | ma.getEnclosingStmt().getEnclosingStmt*() = cc.getTry() and ma.getMethod().getAThrownExceptionType() = ex)
			and
			exists(Expr loopReentry, ControlFlowNode last | 
				if exists(loop.(ForStmt).getAnUpdate())
				then loopReentry = loop.(ForStmt).getUpdate(0)
				else loopReentry = loop.getCondition() 
			|
				last.getEnclosingStmt().getEnclosingStmt*() = cc.getBlock() and
				hasSuccessor(last, loopReentry)
			))
			
}

predicate isCaughtImplicitlyAndRetried(LoopStmt loop, RefType ex) {
	not isCaughtExactlyAndRetried(loop, ex) and 
	exists(CatchClause cc | isCaughtTopLevel(loop,cc) 
			and
			cc.getACaughtType() != ex and cc.getACaughtType().getADescendant() = ex 
			and
			exists(MethodAccess ma | ma.getEnclosingStmt().getEnclosingStmt*() = cc.getTry() and ma.getMethod().getAThrownExceptionType() = ex)
			and
			exists(Expr loopReentry, ControlFlowNode last | 
				if exists(loop.(ForStmt).getAnUpdate())
				then loopReentry = loop.(ForStmt).getUpdate(0)
				else loopReentry = loop.getCondition() 
			|
				last.getEnclosingStmt().getEnclosingStmt*() = cc.getBlock() and
				hasSuccessor(last, loopReentry)
			))
			
}

predicate isCaughtExactlyAndNotRetried(LoopStmt loop, RefType ex) {
	exists(CatchClause cc | isCaughtTopLevel(loop,cc) 
			and
			cc.getACaughtType() = ex 
			and
			exists(MethodAccess ma | ma.getEnclosingStmt().getEnclosingStmt*() = cc.getTry() and ma.getMethod().getAThrownExceptionType() = ex)
			and
			not exists(Expr loopReentry, ControlFlowNode last | 
				if exists(loop.(ForStmt).getAnUpdate())
				then loopReentry = loop.(ForStmt).getUpdate(0)
				else loopReentry = loop.getCondition() 
			|
				last.getEnclosingStmt().getEnclosingStmt*() = cc.getBlock() and
				hasSuccessor(last, loopReentry)
			))
}

predicate isCaughtImplicitlyAndNotRetried(LoopStmt loop, RefType ex) {
	not isCaughtExactlyAndNotRetried(loop, ex) and
	exists(CatchClause cc | isCaughtTopLevel(loop,cc) 
			and
			cc.getACaughtType() != ex and cc.getACaughtType().getADescendant() = ex 
			and
			exists(MethodAccess ma | ma.getEnclosingStmt().getEnclosingStmt*() = cc.getTry() and ma.getMethod().getAThrownExceptionType() = ex)
			and
			not exists(Expr loopReentry, ControlFlowNode last | 
				if exists(loop.(ForStmt).getAnUpdate())
				then loopReentry = loop.(ForStmt).getUpdate(0)
				else loopReentry = loop.getCondition() 
			|
				last.getEnclosingStmt().getEnclosingStmt*() = cc.getBlock() and
				hasSuccessor(last, loopReentry)
			))
}

predicate isNotCaught(LoopStmt loop, RefType ex) {
	exists(MethodAccess ma | ma.getAnEnclosingStmt() = loop and ma.getMethod().getAThrownExceptionType() = ex and
			not exists(CatchClause cc | ma.getAnEnclosingStmt() = cc) and
			not exists(CatchClause cc | ma.getAnEnclosingStmt() = cc.getTry() and cc.getEnclosingStmt*() = loop and cc.getACaughtType().getADescendant() = ex))
			
}

string getMethodList(LoopStmt loop, RefType ex) {
	result = "(" + concat(MethodAccess ma | 
							ma.getAnEnclosingStmt() = loop and 
							ma.getMethod().getAThrownExceptionType() = ex and
							not exists(CatchClause cc | ma.getAnEnclosingStmt() = cc) 
					| ma.getMethod().getName()+"#"+ma.getLocation().getStartLine(), ";") + ")"
}


/*
from LoopStmt l 
where 
	isSource(l)
		and
	isRetryLoop(l)
select l.getLocation().(GithubLocation).getGithubURL(),
	concat(RefType t | isCaughtExactlyAndRetried(l,t) | t.toString(), " | "),
	concat(RefType t | isCaughtExactlyAndNotRetried(l,t) | t.toString(), " | "),
	concat(RefType t | isNotCaught(l,t) | t.toString(), " | "),
*/


from ThrowableType tt
where 
		count(LoopStmt loop | isSource(loop) and isRetryLoop(loop) and isCaughtExactlyAndRetried(loop, tt) | loop) > 0 or
		count(LoopStmt loop | isSource(loop) and isRetryLoop(loop) and isCaughtImplicitlyAndRetried(loop, tt) | loop) > 0 or
		count(LoopStmt loop | isSource(loop) and isRetryLoop(loop) and isCaughtExactlyAndNotRetried(loop, tt) | loop) > 0 or 
		count(LoopStmt loop | isSource(loop) and isRetryLoop(loop) and isCaughtImplicitlyAndNotRetried(loop, tt) | loop) > 0 or 
		count(LoopStmt loop | isSource(loop) and isRetryLoop(loop) and isNotCaught(loop, tt) | loop) > 0
select tt.getQualifiedName(),
		count(LoopStmt loop | isSource(loop) and isRetryLoop(loop) and isCaughtExactlyAndRetried(loop, tt) | loop), 
		count(LoopStmt loop | isSource(loop) and isRetryLoop(loop) and isCaughtImplicitlyAndRetried(loop, tt) | loop),
		count(LoopStmt loop | isSource(loop) and isRetryLoop(loop) and isCaughtExactlyAndNotRetried(loop, tt) | loop), 
		count(LoopStmt loop | isSource(loop) and isRetryLoop(loop) and isCaughtImplicitlyAndNotRetried(loop, tt) | loop), 
		count(LoopStmt loop | isSource(loop) and isRetryLoop(loop) and isNotCaught(loop, tt) | loop),
		concat(LoopStmt loop | isSource(loop) and isRetryLoop(loop) and isCaughtExactlyAndRetried(loop, tt) | loop.getLocation().(GithubLocation).getGithubURL()+" "+getMethodList(loop,tt), " | "), 
		concat(LoopStmt loop | isSource(loop) and isRetryLoop(loop) and isCaughtImplicitlyAndRetried(loop, tt) | loop.getLocation().(GithubLocation).getGithubURL()+" "+getMethodList(loop,tt), " | "),
		concat(LoopStmt loop | isSource(loop) and isRetryLoop(loop) and isCaughtExactlyAndNotRetried(loop, tt) | loop.getLocation().(GithubLocation).getGithubURL()+" "+getMethodList(loop,tt), " | "), 
		concat(LoopStmt loop | isSource(loop) and isRetryLoop(loop) and isCaughtImplicitlyAndNotRetried(loop, tt) | loop.getLocation().(GithubLocation).getGithubURL()+" "+getMethodList(loop,tt), " | "), 
		concat(LoopStmt loop | isSource(loop) and isRetryLoop(loop) and isNotCaught(loop, tt) | loop.getLocation().(GithubLocation).getGithubURL()+" "+getMethodList(loop,tt), " | ")
