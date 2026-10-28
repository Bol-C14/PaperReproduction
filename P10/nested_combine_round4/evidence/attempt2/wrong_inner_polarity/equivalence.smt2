; benchmark generated from python API
(set-info :status unknown)
(declare-fun c () (_ BitVec 8))
(declare-fun b () (_ BitVec 8))
(declare-fun a () (_ BitVec 8))
(assert
 (let ((?x10 (bvadd ((_ extract 7 0) (bvmul ((_ extract 7 0) a) ((_ extract 7 0) b))) ((_ extract 7 0) (_ bv1 8)))))
(let (($x25 (and (distinct (ite (= (ite (bvult b (_ bv4 8)) (_ bv1 1) (_ bv0 1)) (_ bv0 1)) (_ bv1 1) (_ bv0 1)) (_ bv0 1)) true)))
(let (($x7 (and (distinct (ite (bvult a (_ bv8 8)) (_ bv1 1) (_ bv0 1)) (_ bv0 1)) true)))
(let ((?x96 (ite $x7 (ite (and (distinct (ite (bvult b (_ bv4 8)) (_ bv1 1) (_ bv0 1)) (_ bv0 1)) true) ?x10 c) c)))
(and (distinct ?x96 (ite $x7 (ite $x25 ?x10 c) c)) true))))))
(check-sat)
