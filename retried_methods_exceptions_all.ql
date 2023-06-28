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


private predicate caughtInside(TryStmt t, Stmt s, RefType rt) {
  exists(TryStmt innerTry | innerTry.getEnclosingStmt+() = t.getBlock() |
    s.getEnclosingStmt+() = innerTry.getBlock() and
    caughtType(innerTry, _).hasSubtype*(rt)
  )
}


private predicate caught(TryStmt t, Stmt s, RefType rt) {
	(s.getEnclosingStmt+()=t.getBlock() and caughtType(t,_).hasSubtype*(rt))
}

private RefType caughtType(TryStmt try, int index) {
  exists(CatchClause cc | cc = try.getCatchClause(index) |
    if cc.isMultiCatch()
    then result = cc.getVariable().getTypeAccess().(UnionTypeAccess).getAnAlternative().getType()
    else result = cc.getVariable().getType()
  )
}

private predicate maybeUnchecked(RefType t) {
  t.getAnAncestor().hasQualifiedName("java.lang", "RuntimeException") or
  t.getAnAncestor().hasQualifiedName("java.lang", "Error") or
  t.hasQualifiedName("java.lang", "Exception") or
  t.hasQualifiedName("java.lang", "Throwable")
}

RefType getAllThrownExceptionTypes(Method m) {
	exists(RefType type | type = m.getAThrownExceptionType() and result=type) 
	or
	exists(RefType type, ThrowStmt ts | ts.getEnclosingCallable()=m and type=ts.getThrownExceptionType() and not exists(TryStmt try | try.getEnclosingCallable() = m and ts.getEnclosingStmt*() = try and caught(try, ts, type)) and result = type)
	or
	exists(RefType type, MethodAccess ma | ma.getEnclosingCallable()=m and type=getAllThrownExceptionTypes(ma.getMethod()) and not exists(TryStmt try | ma.getAnEnclosingStmt() = try and caught(try, ma.getEnclosingStmt(), type)) and result=type)
}


boolean inSignature(Method m, RefType type) {
	if m.getAnException().getType()=type
	then result=true
	else result=false
}

boolean isRuntimeException(RefType type) {
	if type.getAnAncestor().hasQualifiedName("java.lang", "RuntimeException") 
	then result=true
	else result=false

}

predicate insideCatchOrFinally(Expr e) {
    exists(CatchClause cc | e.getAnEnclosingStmt() = cc) or 
    exists(TryStmt ts | e.getAnEnclosingStmt() = ts.getFinally())
}


from Method m, RefType type
where 
	type = getAllThrownExceptionTypes(m) and
	exists(LoopStmt loop, MethodAccess ma | loop.getFile().isJavaSourceFile() and isRetryLoop(loop) and ma.getAnEnclosingStmt()=loop and ma.getMethod()=m and not insideCatchOrFinally(ma)) and
	not m.getQualifiedName().matches("java%") 
select appName(), m.getQualifiedName(), type.getQualifiedName(), inSignature(m, type),isRuntimeException(type)

