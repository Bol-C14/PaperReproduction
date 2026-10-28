; benchmark generated from python API
(set-info :status unknown)
(declare-fun c () (_ BitVec 16))
(declare-fun b () (_ BitVec 16))
(declare-fun a () (_ BitVec 16))
(assert
 (let ((?x230 ((_ extract 15 0) ((_ extract 15 0) ((_ extract 15 0) ((_ extract 15 0) ((_ extract 15 0) ((_ extract 15 0) ((_ extract 15 0) c)))))))))
(let ((?x50 ((_ extract 15 0) ((_ extract 15 0) ((_ extract 15 0) ((_ extract 15 0) ((_ extract 15 0) ((_ extract 15 0) ((_ extract 15 0) b)))))))))
(let ((?x31 ((_ extract 15 0) ((_ extract 15 0) ((_ extract 15 0) a)))))
(let ((?x118 ((_ extract 15 0) ((_ extract 15 0) ((_ extract 15 0) ((_ extract 15 0) (ite (bvslt ?x31 (_ bv0 16)) (bvneg ?x31) ?x31)))))))
(let (($x90 (and (distinct (ite (bvsge a (_ bv0 16)) (_ bv1 1) (_ bv0 1)) (_ bv0 1)) true)))
(let ((?x19 (ite $x90 (bvadd ((_ extract 15 0) (ite (bvslt a (_ bv0 16)) (bvneg a) a)) ((_ extract 15 0) b)) c)))
(and (distinct ?x19 (ite $x90 (bvadd ((_ extract 15 0) ?x118) ((_ extract 15 0) ?x50)) ?x230)) true))))))))
(check-sat)
