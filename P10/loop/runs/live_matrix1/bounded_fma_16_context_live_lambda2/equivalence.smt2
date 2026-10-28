; benchmark generated from python API
(set-info :status unknown)
(declare-fun c () (_ BitVec 16))
(declare-fun b () (_ BitVec 16))
(declare-fun a () (_ BitVec 16))
(assert
 (let ((?x36 (bvmul ((_ extract 15 0) ((_ extract 15 0) ((_ extract 15 0) ((_ extract 15 0) a)))) ((_ extract 15 0) ((_ extract 15 0) ((_ extract 15 0) ((_ extract 15 0) b)))))))
(let ((?x54 ((_ extract 15 0) ((_ extract 15 0) ((_ extract 15 0) ((_ extract 15 0) ((_ extract 15 0) ((_ extract 15 0) ((_ extract 15 0) c)))))))))
(let (($x16 (and (distinct (ite (bvult a (_ bv8 16)) (_ bv1 1) (_ bv0 1)) (_ bv0 1)) true)))
(let ((?x80 (ite $x16 (bvadd ?x54 ((_ extract 15 0) ((_ extract 15 0) ((_ extract 15 0) ((_ extract 15 0) ?x36))))) c)))
(let ((?x72 (ite $x16 (bvadd ((_ extract 15 0) (bvmul ((_ extract 15 0) a) ((_ extract 15 0) b))) ((_ extract 15 0) c)) c)))
(and (distinct ?x72 ?x80) true)))))))
(check-sat)
