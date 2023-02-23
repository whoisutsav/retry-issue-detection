/**
 * @kind problem
 * @id WHEN-too-soon 
 * @problem.severity warning
 */

import java

class IncrementExpr extends Expr {
  IncrementExpr() {
    // x += e
    this instanceof AssignAddExpr
    or
    // ++x or x++
    this instanceof PreIncExpr
    or
    this instanceof PostIncExpr
    or
	// --x or x--
	this instanceof PreDecExpr
	or 
	this instanceof PostDecExpr
    or
    // x = x + e
    exists(AssignExpr assgn, Variable v | assgn = this |
      assgn.getDest() = v.getAnAccess() and
      assgn.getRhs().(AddExpr).getAnOperand().getUnderlyingExpr() = v.getAnAccess()
    )
  }
}

class GithubLocation extends Location {
  string getGithubURL() {
  	result = "https://github.com/%%GITHUB_NAMESPACE%%/tree/" + "/" + 
				"%%COMMIT_SHA%%" + "/" + 
				this.toString().replaceAll("file:///opt/src", "").regexpReplaceAll(":(\\d+):\\d+:\\d+:\\d+$", "#L$1")
  }
}

predicate isRetryLoop(LoopStmt l) {
  /* exists(VarAccess va | va.getVariable().getName().toLowerCase().matches("%retry%")
			and va.getAnEnclosingStmt() = l) or
  exists(StringLiteral sl | sl.getValue().toLowerCase().matches("%retry%"))
*/

  (not l instanceof EnhancedForStmt)
    and
  exists(Expr e | e.getAnEnclosingStmt() = l and e.toString().toLowerCase().matches("%retry%"))
	and
  (hasExceptionHandling(l) or exists(Exception e | e.getName() != "InterruptedException" and e = l.getEnclosingCallable().getAnException()))
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

predicate hasCapOnRetries(LoopStmt st) {
	(st.getCondition() instanceof ComparisonExpr 
		or st.getCondition().getAChildExpr() instanceof ComparisonExpr)
		or
	exists(IfStmt is | is.getEnclosingStmt*() = st and (is.getCondition().toString().toLowerCase().matches("%retry%") or is.getCondition().getAChildExpr().toString().toLowerCase().matches("%retry%")))
}


predicate hasCapOnRetries2(LoopStmt st) {
  exists(ComparisonExpr ce, IncrementExpr ie, Variable v | 
			ce.getAnEnclosingStmt() = st and ie.getAnEnclosingStmt() = st and
			ce.getAChildExpr() = v.getAnAccess() and ie.getAChildExpr() = v.getAnAccess())
}


from LoopStmt st 
where isRetryLoop(st) and
not hasCapOnRetries(st) and
isSource(st)
select st.getLocation().(GithubLocation).getGithubURL()
