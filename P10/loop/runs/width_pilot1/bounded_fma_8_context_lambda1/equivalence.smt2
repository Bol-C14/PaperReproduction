; benchmark generated from python API
(set-info :status unknown)
(declare-fun c () (_ BitVec 8))
(declare-fun b () (_ BitVec 8))
(declare-fun a () (_ BitVec 8))
(assert
 (let ((?x38 ((_ extract 7 0) ((_ extract 7 0) ((_ extract 7 0) ((_ extract 7 0) ((_ extract 7 0) ((_ extract 7 0) ((_ extract 7 0) c)))))))))
(let ((?x39 ((_ extract 7 0) ((_ extract 7 0) ((_ extract 7 0) c)))))
(let ((?x33 (bvmul ((_ zero_extend 5) ((_ extract 2 0) ((_ extract 7 0) a))) ((_ extract 7 0) ((_ extract 7 0) ((_ extract 7 0) b))))))
(let ((?x44 ((_ extract 7 0) ((_ extract 7 0) ((_ extract 7 0) (bvadd ((_ extract 7 0) ((_ extract 7 0) ((_ extract 7 0) ?x33))) ?x39))))))
(let (($x17 (and (distinct (ite (bvult a (_ bv8 8)) (_ bv1 1) (_ bv0 1)) (_ bv0 1)) true)))
(let ((?x20 (ite $x17 (bvadd ((_ extract 7 0) (bvmul ((_ extract 7 0) a) ((_ extract 7 0) b))) ((_ extract 7 0) c)) c)))
(and (distinct ?x20 (ite $x17 ((_ extract 7 0) ((_ extract 7 0) ((_ extract 7 0) ?x44))) ((_ extract 7 0) ?x38))) true))))))))
(check-sat)
