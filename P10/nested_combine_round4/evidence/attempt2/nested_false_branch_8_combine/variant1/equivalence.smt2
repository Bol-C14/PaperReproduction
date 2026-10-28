; benchmark generated from python API
(set-info :status unknown)
(declare-fun c () (_ BitVec 8))
(declare-fun a () (_ BitVec 8))
(declare-fun b () (_ BitVec 8))
(assert
 (let ((?x27 (bvmul ((_ zero_extend 4) ((_ extract 2 0) ((_ extract 2 0) ((_ extract 2 0) b)))) ((_ zero_extend 3) ((_ extract 3 0) ((_ extract 7 0) a))))))
(let (($x53 (and (distinct (ite (bvult a (_ bv4 8)) (_ bv1 1) (_ bv0 1)) (_ bv0 1)) true)))
(let (($x55 (and (distinct (ite (bvult a (_ bv16 8)) (_ bv1 1) (_ bv0 1)) (_ bv0 1)) true)))
(let ((?x9 (ite $x55 (ite $x53 c (bvmul ((_ extract 7 0) a) ((_ zero_extend 5) ((_ extract 2 0) b)))) c)))
(and (distinct ?x9 (ite $x55 (ite $x53 ((_ extract 7 0) c) ((_ zero_extend 1) ?x27)) c)) true))))))
(check-sat)
