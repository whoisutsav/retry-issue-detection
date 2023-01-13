/**
 * @kind problem
 * @id WHEN-too-soon 
 * @problem.severity warning
 */

import java

class GithubLocation extends Location {
  string getGithubURL() {
  	result = "https://github.com/apache/hive/tree/" + "/" + 
				"e427ce0" + "/" + 
				this.toString().replaceAll("file:///opt/src", "").regexpReplaceAll(":(\\d+):\\d+:\\d+:\\d+$", "#L$1")
  }
}

predicate isRetryLoop(LoopStmt l) {
  /* exists(VarAccess va | va.getVariable().getName().toLowerCase().matches("%retry%")
			and va.getAnEnclosingStmt() = l) or
  exists(StringLiteral sl | sl.getValue().toLowerCase().matches("%retry%"))
*/

  exists(Expr e | e.getAnEnclosingStmt() = l and e.toString().toLowerCase().matches("%retry%"))
}

/*predicate hasSleep(LoopStmt l) {
  exists(MethodAccess m | m.getMethod().hasQualifiedName("java.lang", "Thread", "sleep") and m.getAnEnclosingStmt() = l)
}*/

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

from LoopStmt st 
where isRetryLoop(st) and
not hasCapOnRetries(st) and
isSource(st)
select st.getLocation().(GithubLocation).getGithubURL()
