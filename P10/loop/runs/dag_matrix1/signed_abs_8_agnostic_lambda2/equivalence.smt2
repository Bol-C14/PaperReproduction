; benchmark generated from python API
(set-info :status unknown)
(declare-fun c () (_ BitVec 8))
(declare-fun a () (_ BitVec 8))
(declare-fun b () (_ BitVec 8))
(assert
 (let (($x11 (and (distinct (ite (bvsge a (_ bv0 8)) (_ bv1 1) (_ bv0 1)) (_ bv0 1)) true)))
(let ((?x70 (ite $x11 (bvadd ((_ extract 7 0) b) ((_ extract 7 0) (ite (bvslt a (_ bv0 8)) (bvneg a) a))) c)))
(let ((?x161 (ite $x11 (bvadd ((_ extract 7 0) (ite (bvslt a (_ bv0 8)) (bvneg a) a)) ((_ extract 7 0) b)) c)))
(and (distinct ?x161 ?x70) true)))))
(check-sat)
