; benchmark generated from python API
(set-info :status unknown)
(declare-fun c () (_ BitVec 16))
(declare-fun b () (_ BitVec 16))
(declare-fun a () (_ BitVec 16))
(assert
 (let (($x12 (and (distinct (ite (bvsge a (_ bv0 16)) (_ bv1 1) (_ bv0 1)) (_ bv0 1)) true)))
(let ((?x13 (ite $x12 (bvadd ((_ extract 15 0) ((_ extract 15 0) a)) ((_ extract 15 0) ((_ extract 15 0) b))) ((_ extract 15 0) c))))
(let ((?x17 (ite $x12 (bvadd ((_ extract 15 0) (ite (bvslt a (_ bv0 16)) (bvneg a) a)) ((_ extract 15 0) b)) c)))
(and (distinct ?x17 ?x13) true)))))
(check-sat)
