; benchmark generated from python API
(set-info :status unknown)
(declare-fun c () (_ BitVec 16))
(declare-fun b () (_ BitVec 16))
(declare-fun a () (_ BitVec 16))
(assert
 (let ((?x1006 (bvmul ((_ zero_extend 3) ((_ extract 3 0) ((_ extract 15 0) a))) ((_ zero_extend 4) ((_ extract 2 0) ((_ extract 2 0) ((_ extract 2 0) b)))))))
(let (($x32 (and (distinct (ite (bvult a (_ bv4 16)) (_ bv1 1) (_ bv0 1)) (_ bv0 1)) true)))
(let (($x6 (and (distinct (ite (bvult a (_ bv16 16)) (_ bv1 1) (_ bv0 1)) (_ bv0 1)) true)))
(let ((?x55 (ite $x6 (ite $x32 c (bvmul ((_ extract 15 0) a) ((_ zero_extend 13) ((_ extract 2 0) b)))) c)))
(and (distinct ?x55 (ite $x6 (ite $x32 ((_ extract 15 0) c) ((_ zero_extend 9) ?x1006)) c)) true))))))
(check-sat)
