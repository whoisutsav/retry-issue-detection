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

predicate containsTryCatch(LoopStmt st) {
	exists(CatchClause cc | cc.getEnclosingStmt*() = st)
}

from WhileStmt st
where lacksComparisonCondition(st)
and containsTryCatch(st) and
isSource(st)
select st.getLocation().(GithubLocation).getGithubURL()
