; benchmark generated from python API
(set-info :status unknown)
(declare-fun c () (_ BitVec 16))
(declare-fun b () (_ BitVec 16))
(declare-fun a () (_ BitVec 16))
(assert
 (let ((?x82 ((_ extract 15 0) ((_ extract 15 0) ((_ extract 15 0) ((_ extract 15 0) ((_ extract 15 0) ((_ extract 15 0) ((_ extract 15 0) b)))))))))
(let ((?x72 ((_ extract 14 0) ((_ extract 15 0) ((_ extract 15 0) ((_ extract 15 0) ((_ extract 15 0) ((_ extract 15 0) ((_ extract 15 0) a)))))))))
(let (($x40 (and (distinct (ite (bvsge a (_ bv0 16)) (_ bv1 1) (_ bv0 1)) (_ bv0 1)) true)))
(let ((?x25 (ite $x40 (bvadd ((_ extract 15 0) (ite (bvslt a (_ bv0 16)) (bvneg a) a)) ((_ extract 15 0) b)) c)))
(and (distinct ?x25 (ite $x40 ((_ extract 15 0) (bvadd ((_ zero_extend 1) ?x72) ((_ extract 15 0) ?x82))) c)) true))))))
(check-sat)
