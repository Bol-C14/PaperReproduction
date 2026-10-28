; benchmark generated from python API
(set-info :status unknown)
(declare-fun c () (_ BitVec 16))
(declare-fun a () (_ BitVec 16))
(declare-fun b () (_ BitVec 16))
(assert
 (let ((?x92 ((_ extract 15 0) ((_ extract 15 0) ((_ extract 15 0) ((_ extract 15 0) ((_ extract 15 0) ((_ extract 15 0) ((_ extract 15 0) c)))))))))
(let ((?x35 (bvmul ((_ extract 15 0) ((_ extract 15 0) ((_ extract 15 0) ((_ extract 15 0) ((_ extract 15 0) ((_ extract 15 0) b)))))) ((_ zero_extend 13) ((_ extract 2 0) ((_ extract 15 0) ((_ extract 15 0) ((_ extract 15 0) ((_ extract 15 0) a)))))))))
(let ((?x61 (bvadd ((_ extract 15 0) ((_ extract 15 0) ((_ extract 15 0) ((_ extract 15 0) ((_ extract 15 0) ?x35))))) ((_ extract 15 0) ?x92))))
(let (($x16 (and (distinct (ite (bvult a (_ bv8 16)) (_ bv1 1) (_ bv0 1)) (_ bv0 1)) true)))
(let ((?x72 (ite $x16 (bvadd ((_ extract 15 0) (bvmul ((_ extract 15 0) a) ((_ extract 15 0) b))) ((_ extract 15 0) c)) c)))
(and (distinct ?x72 (ite $x16 ((_ extract 15 0) ?x61) c)) true)))))))
(check-sat)
