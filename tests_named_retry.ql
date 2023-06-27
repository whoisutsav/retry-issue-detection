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

predicate isRetryTest(TestMethod m) {
	m.getName().toLowerCase().matches("%retry%") or m.getName().toLowerCase().matches("%retries%")
}

//select avg(TestMethod m | isRetryTest(m) | m.getTotalNumberOfLines()), avg(TestMethod m | not isRetryTest(m) | m.getTotalNumberOfLines()) 

from TestMethod m
where isRetryTest(m)
select m.getLocation().getFile().getRelativePath(),
        m.getLocation().getStartLine(),
        m.getBody().getLocation().getEndLine(),
        m.getLocation().(GithubLocation).getGithubURL()
