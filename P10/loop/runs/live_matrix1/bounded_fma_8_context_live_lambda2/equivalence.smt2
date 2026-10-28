; benchmark generated from python API
(set-info :status unknown)
(declare-fun c () (_ BitVec 8))
(declare-fun b () (_ BitVec 8))
(declare-fun a () (_ BitVec 8))
(assert
 (let ((?x17 (bvadd ((_ extract 7 0) ((_ extract 7 0) ((_ extract 7 0) (bvmul ((_ extract 7 0) a) ((_ extract 7 0) b))))) ((_ extract 7 0) ((_ extract 7 0) ((_ extract 7 0) c))))))
(let (($x6 (and (distinct (ite (bvult a (_ bv8 8)) (_ bv1 1) (_ bv0 1)) (_ bv0 1)) true)))
(let ((?x65 (ite $x6 (bvadd ((_ extract 7 0) (bvmul ((_ extract 7 0) a) ((_ extract 7 0) b))) ((_ extract 7 0) c)) c)))
(and (distinct ?x65 (ite $x6 ?x17 c)) true)))))
(check-sat)
