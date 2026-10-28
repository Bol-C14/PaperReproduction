; benchmark generated from python API
(set-info :status unknown)
(declare-fun c () (_ BitVec 8))
(declare-fun b () (_ BitVec 8))
(declare-fun a () (_ BitVec 8))
(assert
 (let ((?x67 ((_ extract 7 0) ((_ extract 7 0) ((_ extract 7 0) ((_ extract 7 0) ((_ extract 7 0) ((_ extract 7 0) ((_ extract 7 0) c)))))))))
(let ((?x30 ((_ extract 7 0) ?x67)))
(let ((?x37 (bvmul ((_ extract 7 0) ((_ extract 7 0) ((_ extract 7 0) a))) ((_ extract 7 0) ((_ extract 7 0) ((_ extract 7 0) b))))))
(let ((?x58 ((_ extract 7 0) ((_ extract 7 0) ((_ extract 7 0) ((_ extract 7 0) ((_ extract 7 0) ((_ extract 7 0) ((_ extract 7 0) ?x37)))))))))
(let (($x14 (and (distinct (ite (bvult a (_ bv8 8)) (_ bv1 1) (_ bv0 1)) (_ bv0 1)) true)))
(let ((?x20 (ite $x14 (bvadd ((_ extract 7 0) (bvmul ((_ extract 7 0) a) ((_ extract 7 0) b))) ((_ extract 7 0) c)) c)))
(and (distinct ?x20 (ite $x14 (bvadd ?x58 ((_ extract 7 0) ?x30)) ?x30)) true))))))))
(check-sat)
