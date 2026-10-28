; benchmark generated from python API
(set-info :status unknown)
(declare-fun c () (_ BitVec 8))
(declare-fun a () (_ BitVec 8))
(declare-fun b () (_ BitVec 8))
(assert
 (let ((?x41 (bvmul ((_ zero_extend 6) ((_ extract 1 0) ((_ extract 7 0) ((_ extract 7 0) b)))) ((_ extract 7 0) ((_ extract 7 0) ((_ extract 7 0) ((_ extract 7 0) a)))))))
(let ((?x67 (bvadd ((_ extract 7 0) ((_ extract 7 0) ((_ extract 7 0) ((_ extract 7 0) ((_ extract 7 0) ?x41))))) ((_ zero_extend 7) ((_ extract 0 0) ((_ extract 7 0) ((_ extract 7 0) ((_ extract 7 0) ((_ extract 7 0) (_ bv1 8))))))))))
(let (($x39 (and (distinct (ite (bvult b (_ bv4 8)) (_ bv1 1) (_ bv0 1)) (_ bv0 1)) true)))
(let (($x10 (and (distinct (ite (bvult a (_ bv8 8)) (_ bv1 1) (_ bv0 1)) (_ bv0 1)) true)))
(let ((?x62 (ite $x10 (ite $x39 ((_ extract 7 0) ((_ extract 7 0) ((_ extract 7 0) ?x67))) ((_ extract 7 0) c)) c)))
(let ((?x55 (ite $x39 (bvadd ((_ extract 7 0) (bvmul ((_ extract 7 0) a) ((_ extract 7 0) b))) ((_ extract 7 0) (_ bv1 8))) c)))
(and (distinct (ite $x10 ?x55 c) ?x62) true))))))))
(check-sat)
