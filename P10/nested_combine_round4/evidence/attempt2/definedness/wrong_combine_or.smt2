; benchmark generated from python API
(set-info :status unknown)
(declare-fun a () (_ BitVec 8))
(declare-fun q () (_ BitVec 1))
(declare-fun p () (_ BitVec 1))
(assert
 (let (($x14 (and (and (distinct (ite (= p (_ bv0 1)) (_ bv1 1) (_ bv0 1)) (_ bv0 1)) true) (and (distinct (ite (= q (_ bv0 1)) (_ bv1 1) (_ bv0 1)) (_ bv0 1)) true))))
(let (($x60 (and true (and (and (and true) (and true))) (and (distinct (ite (= (ite $x14 (_ bv1 1) (_ bv0 1)) (_ bv0 1)) (_ bv1 1) (_ bv0 1)) (_ bv0 1)) true))))
(let (($x32 (and (and true true (and (distinct p (_ bv0 1)) true)) true (and (distinct q (_ bv0 1)) true))))
(or (and (distinct $x32 $x60) true) (and $x32 $x60 (and (distinct ((_ extract 7 0) ((_ extract 7 0) a)) ((_ extract 7 0) a)) true)))))))
(check-sat)
