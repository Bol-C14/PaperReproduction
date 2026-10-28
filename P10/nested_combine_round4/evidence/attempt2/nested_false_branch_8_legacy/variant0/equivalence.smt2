; benchmark generated from python API
(set-info :status unknown)
(declare-fun c () (_ BitVec 8))
(declare-fun a () (_ BitVec 8))
(declare-fun b () (_ BitVec 8))
(assert
 (let (($x22 (and (distinct (ite (bvult a (_ bv4 8)) (_ bv1 1) (_ bv0 1)) (_ bv0 1)) true)))
(let ((?x32 ((_ extract 7 0) (ite $x22 c (bvmul ((_ zero_extend 5) ((_ extract 2 0) b)) ((_ extract 7 0) a))))))
(let (($x39 (and (distinct (ite (bvult a (_ bv16 8)) (_ bv1 1) (_ bv0 1)) (_ bv0 1)) true)))
(let ((?x9 (ite $x39 (ite $x22 c (bvmul ((_ extract 7 0) a) ((_ zero_extend 5) ((_ extract 2 0) b)))) c)))
(and (distinct ?x9 (ite $x39 ?x32 c)) true))))))
(check-sat)
