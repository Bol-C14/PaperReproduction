; benchmark generated from python API
(set-info :status unknown)
(declare-fun a () (_ BitVec 8))
(declare-fun q () (_ BitVec 1))
(declare-fun p () (_ BitVec 1))
(assert
 (let (($x17 (and (distinct (ite (and (and (distinct p (_ bv0 1)) true) (and (distinct q (_ bv0 1)) true)) (_ bv1 1) (_ bv0 1)) (_ bv0 1)) true)))
(let (($x18 (and true (and true true) $x17)))
(let (($x11 (and (distinct q (_ bv0 1)) true)))
(let (($x12 (and (and true true (and (distinct p (_ bv0 1)) true)) true $x11)))
(or (and (distinct $x12 $x18) true) (and $x12 $x18 (and (distinct ((_ extract 7 0) ((_ extract 7 0) a)) ((_ extract 7 0) a)) true))))))))
(check-sat)
