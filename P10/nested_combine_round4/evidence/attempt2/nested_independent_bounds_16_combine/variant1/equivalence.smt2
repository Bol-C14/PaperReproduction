; benchmark generated from python API
(set-info :status unknown)
(declare-fun c () (_ BitVec 16))
(declare-fun a () (_ BitVec 16))
(declare-fun b () (_ BitVec 16))
(assert
 (let ((?x66 (bvmul ((_ zero_extend 3) ((_ extract 1 0) ((_ extract 15 0) b))) ((_ zero_extend 2) ((_ extract 2 0) ((_ extract 15 0) a))))))
(let ((?x132 (bvadd ((_ zero_extend 4) ((_ extract 0 0) ((_ extract 15 0) ((_ extract 15 0) (_ bv1 16))))) ((_ extract 4 0) ((_ extract 4 0) ((_ zero_extend 11) ?x66))))))
(let (($x10 (and (distinct (ite (bvult b (_ bv4 16)) (_ bv1 1) (_ bv0 1)) (_ bv0 1)) true)))
(let (($x530 (and (distinct (ite (bvult a (_ bv8 16)) (_ bv1 1) (_ bv0 1)) (_ bv0 1)) true)))
(let ((?x61 (ite $x10 (bvadd ((_ extract 15 0) (bvmul ((_ extract 15 0) a) ((_ extract 15 0) b))) ((_ extract 15 0) (_ bv1 16))) c)))
(and (distinct (ite $x530 ?x61 c) (ite $x530 (ite $x10 ((_ zero_extend 11) ?x132) ((_ extract 15 0) c)) c)) true)))))))
(check-sat)
