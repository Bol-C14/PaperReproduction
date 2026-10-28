; benchmark generated from python API
(set-info :status unknown)
(declare-fun c () (_ BitVec 8))
(declare-fun a () (_ BitVec 8))
(declare-fun b () (_ BitVec 8))
(assert
 (let ((?x516 ((_ extract 7 0) ((_ extract 7 0) ((_ extract 7 0) ((_ extract 7 0) ((_ extract 7 0) ((_ extract 7 0) ((_ extract 7 0) c)))))))))
(let ((?x37 ((_ extract 7 0) ((_ extract 7 0) ((_ extract 7 0) ((_ extract 7 0) ((_ extract 7 0) ((_ extract 7 0) ((_ extract 7 0) a)))))))))
(let ((?x12 ((_ extract 7 0) ((_ extract 7 0) ((_ extract 7 0) ((_ extract 7 0) ((_ extract 7 0) ((_ extract 7 0) ((_ extract 7 0) b)))))))))
(let ((?x147 (bvadd ((_ extract 7 0) ?x12) ((_ extract 7 0) (ite (bvslt ?x37 (_ bv0 8)) (bvneg ?x37) ?x37)))))
(let (($x70 (and (distinct (ite (bvsge a (_ bv0 8)) (_ bv1 1) (_ bv0 1)) (_ bv0 1)) true)))
(let ((?x156 (ite $x70 (bvadd ((_ extract 7 0) (ite (bvslt a (_ bv0 8)) (bvneg a) a)) ((_ extract 7 0) b)) c)))
(and (distinct ?x156 (ite $x70 ?x147 ?x516)) true))))))))
(check-sat)
