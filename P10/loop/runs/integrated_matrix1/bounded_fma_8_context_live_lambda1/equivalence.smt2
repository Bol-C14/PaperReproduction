; benchmark generated from python API
(set-info :status unknown)
(declare-fun c () (_ BitVec 8))
(declare-fun a () (_ BitVec 8))
(declare-fun b () (_ BitVec 8))
(assert
 (let ((?x23 ((_ zero_extend 5) ((_ extract 2 0) ((_ extract 7 0) ((_ extract 7 0) ((_ extract 7 0) ((_ extract 7 0) ((_ extract 7 0) a)))))))))
(let ((?x35 ((_ extract 7 0) ((_ extract 7 0) ((_ extract 7 0) ((_ extract 7 0) ((_ extract 7 0) ((_ extract 7 0) ((_ extract 7 0) b)))))))))
(let ((?x33 (bvadd ((_ extract 7 0) ((_ extract 7 0) (bvmul ?x35 ?x23))) ((_ extract 7 0) ((_ extract 7 0) ((_ extract 7 0) ((_ extract 7 0) ((_ extract 7 0) ((_ extract 7 0) c)))))))))
(let (($x20 (and (distinct (ite (bvult a (_ bv8 8)) (_ bv1 1) (_ bv0 1)) (_ bv0 1)) true)))
(let ((?x65 (ite $x20 (bvadd ((_ extract 7 0) (bvmul ((_ extract 7 0) a) ((_ extract 7 0) b))) ((_ extract 7 0) c)) c)))
(and (distinct ?x65 (ite $x20 ((_ extract 7 0) ((_ extract 7 0) ?x33)) c)) true)))))))
(check-sat)
