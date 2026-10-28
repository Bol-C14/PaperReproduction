; benchmark generated from python API
(set-info :status unknown)
(declare-fun c () (_ BitVec 16))
(declare-fun b () (_ BitVec 16))
(declare-fun a () (_ BitVec 16))
(assert
 (let ((?x25 ((_ extract 15 0) ((_ extract 15 0) ((_ extract 15 0) ((_ extract 15 0) ((_ extract 15 0) ((_ extract 15 0) c))))))))
(let ((?x12 ((_ extract 15 0) ((_ extract 15 0) ((_ extract 15 0) ((_ extract 15 0) ((_ extract 15 0) ((_ extract 15 0) ((_ extract 15 0) b)))))))))
(let ((?x44 ((_ extract 2 0) ((_ extract 15 0) ((_ extract 15 0) ((_ extract 15 0) ((_ extract 15 0) ((_ extract 15 0) ((_ extract 15 0) a)))))))))
(let ((?x28 (bvadd ((_ extract 15 0) ((_ extract 15 0) (bvmul ((_ zero_extend 13) ?x44) ((_ extract 15 0) ?x12)))) ((_ extract 15 0) ?x25))))
(let (($x18 (and (distinct (ite (bvult a (_ bv8 16)) (_ bv1 1) (_ bv0 1)) (_ bv0 1)) true)))
(let ((?x121 (ite $x18 (bvadd ((_ extract 15 0) (bvmul ((_ extract 15 0) a) ((_ extract 15 0) b))) ((_ extract 15 0) c)) c)))
(and (distinct ?x121 (ite $x18 ?x28 ?x25)) true))))))))
(check-sat)
