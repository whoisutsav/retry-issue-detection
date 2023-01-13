/**
 * @kind problem
 * @id while-try-catch 
 * @problem.severity warning
 */

import java

class GithubLocation extends Location {
  string getGithubURL() {
  	result = "https://github.com/apache/hadoop/tree/" + "/" + 
				"ee7d178" + "/" + 
				this.toString().replaceAll("file:///opt/src", "").regexpReplaceAll(":(\\d+):\\d+:\\d+:\\d+$", "#L$1")
  }
}

predicate isSource(Element e) {
 not e.getCompilationUnit().getFile().getRelativePath().toLowerCase().matches("%test%") 
}

predicate lacksComparisonCondition(LoopStmt st) {
  not st.getCondition() instanceof ComparisonExpr or
    not st.getCondition().getAChildExpr() instanceof ComparisonExpr
}

from LoopStmt st, MethodAccess ma
where isSource(st) and
ma.getMethod().getName().toLowerCase().matches("%shouldretry%")
and ma.getAnEnclosingStmt() = st
select ma.getLocation().(GithubLocation).getGithubURL()
