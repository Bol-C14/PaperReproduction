; benchmark generated from python API
(set-info :status unknown)
(declare-fun b () (_ BitVec 8))
(declare-fun a () (_ BitVec 8))
(declare-fun p () (_ BitVec 1))
(assert
 (let (($x52 (and (distinct (ite (and (distinct p (_ bv0 1)) true) a b) (ite (and (distinct p (_ bv0 1)) true) ((_ extract 7 0) a) ((_ extract 7 0) b))) true)))
(let (($x54 (and true (and true) (and (distinct (ite (= p (_ bv0 1)) (_ bv1 1) (_ bv0 1)) (_ bv0 1)) true))))
(let (($x9 (and (distinct p (_ bv0 1)) true)))
(let (($x56 (and true (ite $x9 (and true true $x9) $x54))))
(let (($x31 (and true (ite $x9 true true))))
(or (and (distinct $x31 $x56) true) (and $x31 $x56 $x52))))))))
(check-sat)
