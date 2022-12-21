/**
 * @kind problem
 * @id WHEN-too-soon 
 * @problem.severity warning
 */

import java

predicate isRetryLoop(LoopStmt l) {
  exists(Expr e | e.getAnEnclosingStmt() = l and e.toString().toLowerCase().matches("%retry%"))
}

predicate hasSleep(LoopStmt l) {
  exists(MethodAccess m | m.getMethod().hasQualifiedName("java.lang", "Thread", "sleep") and m.getAnEnclosingStmt() = l)
}

predicate isSource(Element e) {
 not e.getCompilationUnit().getFile().getRelativePath().toLowerCase().matches("%test%") 
}

predicate isJavaMethod(Method m) {
  m.getQualifiedName().matches("java%") or m.getQualifiedName().matches("%slf4j%")
}



from MethodAccess ma1, MethodAccess ma2, LoopStmt l1, LoopStmt l2 
where (ma1 != ma2) and (l1 != l2) and
not isJavaMethod(ma1.getMethod()) and not isJavaMethod(ma2.getMethod()) and
ma1.getAnEnclosingStmt() = l1 and ma2.getAnEnclosingStmt() = l2 and
isRetryLoop(l1) and isRetryLoop(l2) and
isSource(l1) and isSource(l2) and
hasSleep(l1) and not hasSleep(l2)
select ma2.getMethod().getQualifiedName()
//select ma2 
