; benchmark generated from python API
(set-info :status unknown)
(declare-fun c () (_ BitVec 16))
(declare-fun b () (_ BitVec 16))
(declare-fun a () (_ BitVec 16))
(assert
 (let ((?x54 ((_ extract 15 0) ((_ extract 15 0) ((_ extract 15 0) ((_ extract 15 0) ((_ extract 15 0) ((_ extract 15 0) ((_ extract 15 0) c)))))))))
(let ((?x82 ((_ extract 15 0) ((_ extract 15 0) (bvmul ((_ extract 15 0) ((_ extract 15 0) a)) ((_ extract 15 0) ((_ extract 15 0) b)))))))
(let ((?x57 (bvadd ((_ extract 15 0) ((_ extract 15 0) ((_ extract 15 0) ((_ extract 15 0) ((_ extract 15 0) ?x82))))) ((_ extract 15 0) ?x54))))
(let (($x40 (and (distinct (ite (bvult a (_ bv8 16)) (_ bv1 1) (_ bv0 1)) (_ bv0 1)) true)))
(let ((?x72 (ite $x40 (bvadd ((_ extract 15 0) (bvmul ((_ extract 15 0) a) ((_ extract 15 0) b))) ((_ extract 15 0) c)) c)))
(and (distinct ?x72 (ite $x40 ?x57 c)) true)))))))
(check-sat)
