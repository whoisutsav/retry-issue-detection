/**
 * @kind problem
 * @id WHEN-too-soon 
 * @problem.severity warning
 */

import java

predicate isRetryLoop(LoopStmt l) {
  exists(Expr e | e.getAnEnclosingStmt() = l and e.toString().toLowerCase().matches("%retry%"))
}

predicate hasNoBoundOrBackoff(LoopStmt l) {
 ((not l.getCondition() instanceof ComparisonExpr) or 
   					 not exists(MethodAccess m | m.getMethod().hasQualifiedName("java.lang", "Thread", "sleep") and m.getAnEnclosingStmt() = l))
}

predicate isSource(Element e) {
 not e.getCompilationUnit().getFile().getRelativePath().toLowerCase().matches("%test%") 
}

from LoopStmt l
where isRetryLoop(l) and hasNoBoundOrBackoff(l) and isSource(l)
select l
