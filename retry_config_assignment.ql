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

predicate isTest(Element e) {
 e.getCompilationUnit().getFile().getRelativePath().toLowerCase().matches("%test%") 
}

predicate insideAssert(Expr e) {
	exists(MethodAccess ma | ma.getAChildExpr() = e and ma.getMethod().getName().toLowerCase().matches("%assert%"))
}


from VarAccess va, MethodAccess ma 
where isTest(va) and 
	(va.getVariable().getName().matches("%RETRY%") or va.getVariable().getName().toLowerCase().matches("%RETRIES%") or va.getVariable().getName().matches("%ATTEMPT%")) and 
	not va.getVariable().getName().matches("%INTERVAL%") and
	ma.getAChildExpr() = va and ma.getNumArgument() > 1 and (ma.getMethod().getName().matches("set") or ma.getMethod().getName().matches("setInt")) and 
	not insideAssert(va) 
select va.getVariable().getName(), ma.getArgument(1).toString(), ma.getMethod().getQualifiedName(), va.getCompilationUnit().getName(), va.getLocation().(GithubLocation).getGithubURL(), va.getEnclosingStmt().(ExprStmt).getExpr().toString(), va.getEnclosingStmt().(ExprStmt).getExpr().toString().replaceAll(ma.getArgument(1).toString(), "9999"), va.getLocation().getFile().getRelativePath(), va.getLocation().getStartLine(), va.getLocation().getStartColumn() 

/*
from VarAccess va, MethodAccess ma 
where isTest(va) and 
	(va.getVariable().getName().toLowerCase().matches("%retry%") or va.getVariable().getName().toLowerCase().matches("%retries%")) and 
	ma.getAChildExpr() = va and ma.getNumArgument() > 1 and 
	not insideAssert(va) 
select va.getVariable().getName(), ma.getArgument(1).toString(), ma.getMethod().getQualifiedName(), va.getCompilationUnit().getName(), va.getLocation().(GithubLocation).getGithubURL()
*/


/*
from VarAccess va 
where isTest(va) and 
	(va.getVariable().getName().toLowerCase().matches("%retry%") or va.getVariable().getName().toLowerCase().matches("%retries%")) and 
	(exists(MethodAccess ma | ma.getAChildExpr() = va and ma.getNumArgument()=1) or not exists(MethodAccess ma | ma.getAChildExpr() = va)) and 
	not insideAssert(va) 
select va.getVariable().getName(), "?", "N/A", va.getCompilationUnit().getName(), va.getLocation().(GithubLocation).getGithubURL()
*/

/*
from VarAccess va, MethodAccess ma 
where isTest(va) and 
	(va.getVariable().getName().toLowerCase().matches("%attempt%")) and 
	ma.getAChildExpr() = va and ma.getNumArgument() > 1 and 
	not insideAssert(va) 
select va.getVariable().getName(), ma.getArgument(1).toString(), ma.getMethod().getQualifiedName(), va.getCompilationUnit().getName(), va.getLocation().(GithubLocation).getGithubURL()
*/

