; benchmark generated from python API
(set-info :status unknown)
(declare-fun c () (_ BitVec 16))
(declare-fun a () (_ BitVec 16))
(declare-fun b () (_ BitVec 16))
(assert
 (let (($x11 (and (distinct (ite (bvsge a (_ bv0 16)) (_ bv1 1) (_ bv0 1)) (_ bv0 1)) true)))
(let ((?x70 (ite $x11 (bvadd ((_ extract 15 0) b) ((_ extract 15 0) (ite (bvslt a (_ bv0 16)) (bvneg a) a))) c)))
(let ((?x17 (ite $x11 (bvadd ((_ extract 15 0) (ite (bvslt a (_ bv0 16)) (bvneg a) a)) ((_ extract 15 0) b)) c)))
(and (distinct ?x17 ?x70) true)))))
(check-sat)
