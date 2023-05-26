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

boolean isRetried(LoopStmt loop, RefType type) {
	(isCaughtExactlyAndRetried(loop, type) or isCaughtImplicitlyAndRetried(loop, type)) and result=true
		or
	not isCaughtExactlyAndRetried(loop, type) and not isCaughtImplicitlyAndRetried(loop, type) and result=false
}

boolean isNotCoveredInRetryTest(Method m) {
	(not exists(TestMethod tm, MethodAccess ma |
				(tm.getName().toLowerCase().matches("%retry%") or tm.getName().toLowerCase().matches("%retries%"))
				and ma.getEnclosingCallable().getEnclosingCallable*() = tm and ma.getMethod().getAPossibleImplementation() = m) and result=true)
		or
	(exists(TestMethod tm, MethodAccess ma |
				(tm.getName().toLowerCase().matches("%retry%") or tm.getName().toLowerCase().matches("%retries%"))
				and ma.getEnclosingCallable().getEnclosingCallable*() = tm and ma.getMethod().getAPossibleImplementation() = m) and result=false)
}

boolean isNotCoveredInAnyTest(Method m) {
	(not exists(TestMethod tm, MethodAccess ma | ma.getEnclosingCallable().getEnclosingCallable*() = tm and ma.getMethod().getAPossibleImplementation() = m) and result=true)
		or
	(exists(TestMethod tm, MethodAccess ma | ma.getEnclosingCallable().getEnclosingCallable*() = tm and ma.getMethod().getAPossibleImplementation() = m) and result=false)
}

from Method m 
where isSource(m) and m.isPublic() and exists(LoopStmt loop | isRetryLoop(loop) and loop.getEnclosingCallable() = m)
and (isNotCoveredInRetryTest(m)=true or isNotCoveredInAnyTest(m)=true)
select m.getLocation().(GithubLocation).getGithubURL(), m.getQualifiedName(), isNotCoveredInRetryTest(m), isNotCoveredInAnyTest(m)

/*from TestMethod m, MethodAccess ma
where m.getName() = "connectionRetryTimeoutTest" and 
	//ma.getMethod().getQualifiedName() = "org.apache.zookeeper.server.quorum.Learner$LeaderConnector.connectToLeader" and
	ma.getEnclosingCallable().getEnclosingCallable*() = m
select ma.getMethod().getQualifiedName()*/

