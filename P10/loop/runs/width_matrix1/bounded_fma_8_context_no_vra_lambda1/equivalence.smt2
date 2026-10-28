; benchmark generated from python API
(set-info :status unknown)
(declare-fun c () (_ BitVec 8))
(declare-fun a () (_ BitVec 8))
(declare-fun b () (_ BitVec 8))
(assert
 (let ((?x44 ((_ extract 7 0) ((_ extract 7 0) (bvmul ((_ extract 7 0) ((_ extract 7 0) b)) ((_ extract 7 0) ((_ extract 7 0) a)))))))
(let ((?x29 ((_ extract 7 0) ((_ extract 7 0) ((_ extract 7 0) ((_ extract 7 0) c))))))
(let (($x90 (and (distinct (ite (bvult a (_ bv8 8)) (_ bv1 1) (_ bv0 1)) (_ bv0 1)) true)))
(let ((?x36 (ite $x90 ((_ extract 7 0) ((_ extract 7 0) (bvadd ?x29 ((_ extract 7 0) ?x44)))) ((_ extract 7 0) ?x29))))
(let ((?x50 (ite $x90 (bvadd ((_ extract 7 0) (bvmul ((_ extract 7 0) a) ((_ extract 7 0) b))) ((_ extract 7 0) c)) c)))
(and (distinct ?x50 ?x36) true)))))))
(check-sat)
