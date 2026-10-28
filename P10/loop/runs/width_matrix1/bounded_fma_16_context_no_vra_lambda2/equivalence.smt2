; benchmark generated from python API
(set-info :status unknown)
(declare-fun c () (_ BitVec 16))
(declare-fun b () (_ BitVec 16))
(declare-fun a () (_ BitVec 16))
(assert
 (let ((?x16 (bvmul ((_ extract 15 0) ((_ extract 15 0) ((_ extract 15 0) a))) ((_ extract 15 0) ((_ extract 15 0) ((_ extract 15 0) b))))))
(let ((?x37 ((_ extract 15 0) ((_ extract 15 0) ((_ extract 15 0) c)))))
(let (($x90 (and (distinct (ite (bvult a (_ bv8 16)) (_ bv1 1) (_ bv0 1)) (_ bv0 1)) true)))
(let ((?x42 (ite $x90 ((_ extract 15 0) ((_ extract 15 0) ((_ extract 15 0) ((_ extract 15 0) (bvadd ?x37 ((_ extract 15 0) ?x16)))))) ((_ extract 15 0) ((_ extract 15 0) ((_ extract 15 0) ?x37))))))
(let ((?x121 (ite $x90 (bvadd ((_ extract 15 0) (bvmul ((_ extract 15 0) a) ((_ extract 15 0) b))) ((_ extract 15 0) c)) c)))
(and (distinct ?x121 ?x42) true)))))))
(check-sat)
