; benchmark generated from python API
(set-info :status unknown)
(declare-fun a () (_ BitVec 8))
(declare-fun p () (_ BitVec 1))
(assert
 (let (($x53 (and (and (distinct (ite (= p (_ bv0 1)) (_ bv1 1) (_ bv0 1)) (_ bv0 1)) true) (and (distinct p (_ bv0 1)) true))))
(let (($x39 (and true (and (and true) true) (and (distinct (ite $x53 (_ bv1 1) (_ bv0 1)) (_ bv0 1)) true))))
(or (and (distinct $x39 true) true) (and $x39 true (and (distinct (_ bv0 8) ((_ extract 7 0) a)) true))))))
(check-sat)
