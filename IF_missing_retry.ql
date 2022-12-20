/**
 * @kind problem
 * @id IF-missing-retry 
 * @problem.severity warning
 */

import java

predicate isNetworkRequestMethod(Method m) {
  m.hasQualifiedName("org.apache.druid.java.util.http.client", "HttpClient", "go")
}

predicate isRetryLoop(LoopStmt l) {
  exists(Expr e | e.getAnEnclosingStmt() = l and e.toString().toLowerCase().matches("%retry%"))
}

predicate insideLoop(MethodAccess c) {
  exists (LoopStmt ls | c.getAnEnclosingStmt() = ls)
}

predicate neverCalledInLoop(MethodAccess call) {
  not insideLoop(call) and 
    forall(MethodAccess call2 | call2.getMethod().getAPossibleImplementation() = call.getEnclosingCallable() | neverCalledInLoop(call2))
}

from MethodAccess call
where isNetworkRequestMethod(call.getMethod()) and neverCalledInLoop(call)
and not call.getCompilationUnit().getFile().getRelativePath().toLowerCase().matches("%test%")
select call

