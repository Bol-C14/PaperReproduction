; benchmark generated from python API
(set-info :status unknown)
(declare-fun a () (_ BitVec 8))
(declare-fun q () (_ BitVec 1))
(declare-fun p () (_ BitVec 1))
(assert
 (let (($x17 (and (distinct (ite (and (and (distinct p (_ bv0 1)) true) (and (distinct q (_ bv0 1)) true)) (_ bv1 1) (_ bv0 1)) (_ bv0 1)) true)))
(let (($x18 (and true (and true true) $x17)))
(let (($x9 (and (distinct p (_ bv0 1)) true)))
(let (($x46 (and (and (and true true $x9) true (and (distinct q (_ bv0 1)) true)) true $x9)))
(let (($x24 (and $x46 $x18 (and (distinct ((_ extract 7 0) ((_ extract 7 0) ((_ extract 7 0) a))) ((_ extract 7 0) a)) true))))
(or (and (distinct $x46 $x18) true) $x24)))))))
(check-sat)
