; benchmark generated from python API
(set-info :status unknown)
(declare-fun c () (_ BitVec 8))
(declare-fun b () (_ BitVec 8))
(declare-fun a () (_ BitVec 8))
(assert
 (let ((?x15 (bvmul ((_ zero_extend 2) ((_ extract 2 0) ((_ extract 7 0) a))) ((_ zero_extend 3) ((_ extract 1 0) ((_ extract 7 0) b))))))
(let ((?x11 (bvadd ((_ extract 4 0) ((_ extract 4 0) ((_ zero_extend 3) ?x15))) ((_ zero_extend 4) ((_ extract 0 0) ((_ extract 7 0) ((_ extract 7 0) (_ bv1 8))))))))
(let (($x42 (and (distinct (ite (bvult b (_ bv4 8)) (_ bv1 1) (_ bv0 1)) (_ bv0 1)) true)))
(let (($x55 (and (distinct (ite (bvult a (_ bv8 8)) (_ bv1 1) (_ bv0 1)) (_ bv0 1)) true)))
(let ((?x18 (ite $x42 (bvadd ((_ extract 7 0) (bvmul ((_ extract 7 0) a) ((_ extract 7 0) b))) ((_ extract 7 0) (_ bv1 8))) c)))
(and (distinct (ite $x55 ?x18 c) (ite $x55 (ite $x42 ((_ zero_extend 3) ?x11) ((_ extract 7 0) c)) c)) true)))))))
(check-sat)
