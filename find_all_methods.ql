/**
 * @kind problem
 * @id WHEN-too-soon
 * @problem.severity warning
 */

import java

predicate isSource(Element e) {
 not e.getCompilationUnit().getFile().getRelativePath().toLowerCase().matches("%test%")
}

class GithubLocation extends Location {
  string getGithubURL() {
    result = "https://github.com/%%GITHUB_NAMESPACE%%/tree/" + "/" +
                "%%COMMIT_SHA%%" + "/" +
                this.toString().replaceAll("file:///opt/src", "").regexpReplaceAll(":(\\d+):\\d+:\\d+:\\d+$", "#L$1")
  }
}

//from LoopStmt loop
//where isSource(loop) 
//select loop.getLocation().getFile().getRelativePath(), 
//		loop.getLocation().getStartLine(), 
//		loop.getBody().getLocation().getEndLine()

from SrcMethod m
where isSource(m) and not m.isAbstract()
select m.getLocation().getFile().getRelativePath(),
		m.getLocation().getStartLine(),
		m.getBody().getLocation().getEndLine(),
		m.getLocation().(GithubLocation).getGithubURL()
		
