/**
 * @kind problem
 * @id WHEN-too-soon 
 * @problem.severity warning
 */

import java

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


from TestMethod tm
where tm.getName().toLowerCase().matches("%retry%") or tm.getName().toLowerCase().matches("%retries%")
select tm.getName(), tm.getDeclaringType().getName(), tm.getLocation().(GithubLocation).getGithubURL()
