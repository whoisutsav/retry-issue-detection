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
			and va.getAnEnclosingStmt() = l) */

  exists(Expr e | e.getAnEnclosingStmt() = l and e.toString().toLowerCase().matches("%retry%"))
}

predicate hasSleep(Stmt s) {
  exists(MethodAccess m | m.getMethod().hasQualifiedName("java.lang", "Thread", "sleep") and m.getAnEnclosingStmt() = s) 
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

from LoopStmt l 
where isRetryLoop(l) and
not hasSleep(l) and 
not exists(MethodAccess ma | ma.getAnEnclosingStmt() = l and hasSleep(ma.getMethod().getAPossibleImplementation().getBody())) and 
isSource(l)
select l.getLocation().(GithubLocation).getGithubURL()
