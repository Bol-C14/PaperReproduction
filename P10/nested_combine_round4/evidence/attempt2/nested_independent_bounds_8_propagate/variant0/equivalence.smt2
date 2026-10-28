; benchmark generated from python API
(set-info :status unknown)
(declare-fun c () (_ BitVec 8))
(declare-fun a () (_ BitVec 8))
(declare-fun b () (_ BitVec 8))
(assert
 (let ((?x17 (bvmul ((_ zero_extend 6) ((_ extract 1 0) ((_ extract 7 0) b))) ((_ extract 7 0) ((_ extract 7 0) ((_ extract 7 0) a))))))
(let ((?x16 ((_ extract 7 0) ((_ extract 7 0) (bvadd ((_ extract 7 0) ((_ extract 7 0) (_ bv1 8))) ((_ extract 7 0) ((_ extract 7 0) ?x17)))))))
(let (($x46 (and (distinct (ite (bvult b (_ bv4 8)) (_ bv1 1) (_ bv0 1)) (_ bv0 1)) true)))
(let (($x26 (and (distinct (ite (bvult a (_ bv8 8)) (_ bv1 1) (_ bv0 1)) (_ bv0 1)) true)))
(let ((?x10 (ite $x46 (bvadd ((_ extract 7 0) (bvmul ((_ extract 7 0) a) ((_ extract 7 0) b))) ((_ extract 7 0) (_ bv1 8))) c)))
(and (distinct (ite $x26 ?x10 c) (ite $x26 (ite $x46 ((_ extract 7 0) ?x16) ((_ extract 7 0) c)) c)) true)))))))
(check-sat)
