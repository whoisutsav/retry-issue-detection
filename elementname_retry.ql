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

predicate isSource(Element e) {
 not e.getCompilationUnit().getFile().getRelativePath().toLowerCase().matches("%test%") 
}


from Callable c 
where 
	isSource(c)
		and 
	exists(StringLiteral str | str.getEnclosingCallable() = c 
				and 
			(str.toString().toLowerCase().matches("%retry%") or str.toString().toLowerCase().matches("%retries%"))
				and
			not exists(LoopStmt loop | str.getAnEnclosingStmt() = loop))
select c.getLocation().(GithubLocation).getGithubURL()


